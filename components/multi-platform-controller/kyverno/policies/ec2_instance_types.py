from playwright.sync_api import sync_playwright
import yaml

def scrape_ec2_instance_types():
    """Scrape AWS EC2 instance types by category and return as a dictionary."""
    instance_types = {}  
    
    # using PLaywright to acrape data from 
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless mode for CI efficiency
        page = browser.new_page()
        page.goto("https://docs.aws.amazon.com/ec2/latest/instancetypes/instance-types.html")
        print("Opened AWS EC2 Instance Types documentation page.")
        
        # 3. Click the expand button to reveal instance families
        expand_button_selector = "button.awsui_icon-container_gwq0h_5ub0w_264.awsui_expand-button_gwq0h_5ub0w_246"
        try:
            page.locator(expand_button_selector).click(timeout=10000)
            print("Clicked expand button to reveal instance family categories.")
        except Exception as e:
            raise RuntimeError("Failed to find or click the expand button for instance families.") from e
        
        # 4. Locate the container div that holds the list of instance families
        container_selector = "[id=':r39:'] > ul"
        try:
            # Wait for the list to be visible after clicking expand
            page.wait_for_selector(container_selector, timeout=5000)
        except Exception as e:
            raise RuntimeError("Instance family list did not appear after expanding. Page structure may have changed.") from e
        
        # Find all category list items under the container UL
        categories = page.locator(f"{container_selector} > li")
        count = categories.count()
        if count == 0:
            raise RuntimeError("No instance family categories found on the page.")
        
        for i in range(count):
            # For each category list item:
            li = categories.nth(i)
            # 5. Extract category name from the span text
            category_name = li.locator("span").inner_text()
            category_name = category_name.rstrip(":")  # remove trailing colon, if any
            # Use a safe key format for YAML (lowercase and hyphenated)
            key_name = category_name.lower().replace(" ", "-")
            instance_types[key_name] = []  # initialize list for this category
            print(f"Found category: {category_name}")
            
            # 6. Click the link to navigate to the category's details page
            # (anchor <a> is expected inside the list item)
            try:
                # Get the href attribute to verify navigation
                href = li.locator("a").get_attribute("href")
                li.locator("a").click()  # navigate to the details page
                page.wait_for_selector("h2:has-text('Instance families and instance types')", timeout=10000)
                current_url = page.url
            except Exception as e:
                raise RuntimeError(f"Failed to navigate to details page for category '{category_name}'.") from e
            
            # Verify the URL contains the expected path (e.g., .../gp.html for General Purpose)
            expected_fragment = href if href else category_name.lower()
            if expected_fragment not in current_url:
                raise RuntimeError(f"Unexpected URL after clicking {category_name}: {current_url}")
            print(f"Navigated to {category_name} details page: {current_url}")
            
            # 7. Locate the 'Instance families and instance types' section and its table container
            try:
                # Ensure the section heading is present
                page.wait_for_selector("h2:has-text('Instance families and instance types')", timeout=5000)
            except Exception as e:
                raise RuntimeError(f"Section 'Instance families and instance types' not found in {category_name} page.") from e
            
            # Find the table container following the heading
            table_container = page.locator("div.table-container")
            if table_container.count() == 0:
                raise RuntimeError(f"No table found for instance types in {category_name} page.")
            
            # 8. Parse table data to extract all instance types for this category
            rows = table_container.locator("tbody tr")
            for j in range(rows.count()):
                row = rows.nth(j)
                # Get all code elements in the second cell of the row (instance types column)
                code_elems = row.locator("td:nth-child(2) code")
                code_count = code_elems.count()
                for k in range(code_count):
                    instance_type = code_elems.nth(k).inner_text().strip()
                    if instance_type:
                        instance_types[key_name].append(instance_type)
                        print(f"  Added instance type: {instance_type} to category '{category_name}'")
            
            # Navigate back to main page to process the next category
            page.go_back()
            page.wait_for_selector(container_selector)  # ensure the category list is visible again
        
        # Close browser (automatically happens when exiting context manager)
    return instance_types

# Execute the scraping and generate YAML output
if __name__ == "__main__":
    data = scrape_ec2_instance_types()
    # 10. Generate YAML ConfigMap file
    yaml_path = "ec2-instance-types.yaml"
    configmap = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": "ec2-instance-types",
            "namespace": "multi-platform-controller"
        },
        "data": {
            f"instance.type.{k.replace(' ', '.')}": [t for t in v] for k, v in data.items()
            }
        }

    with open(yaml_path, "w") as yf:
        yaml.dump(configmap, yf, default_flow_style=False, sort_keys=False, indent=4, width=100)
    print(f"YAML ConfigMap saved to {yaml_path}")
