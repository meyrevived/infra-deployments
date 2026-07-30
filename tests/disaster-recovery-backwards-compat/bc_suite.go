package disaster_recovery_backwards_compat

import (
	"github.com/konflux-ci/e2e-tests/pkg/framework"
	. "github.com/onsi/ginkgo/v2" //nolint:staticcheck
)

var _ = framework.DisasterRecoverySuiteDescribe("DR Backwards-Compat Suite",
	Label("disaster-recovery-backwards-compat"), Serial, Ordered, func() {
		defineBackwardsCompatSpecs()
	})
