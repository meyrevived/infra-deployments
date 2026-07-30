package disaster_recovery_backwards_compat

import (
	"testing"

	. "github.com/onsi/ginkgo/v2" //nolint:staticcheck
	. "github.com/onsi/gomega"    //nolint:staticcheck
)

func TestDRBackwardsCompat(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "DR backwards-compat backup/restore e2e suite")
}
