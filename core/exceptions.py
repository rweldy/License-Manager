# Copyright @ 2023 Overland Storage, Inc. dba Overland-Tandberg. All rights reserved.
class LicenseServiceException(BaseException):
    pass

class NotFoundException(LicenseServiceException):
    pass

class CouldNotReachLicenseSpringException(LicenseServiceException):
    pass