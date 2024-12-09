# Define dictionary
open_ont_dict = {}


def add_open_ont(ontology_key: str, ranges_dict, subclass_dict, sameas_dict):
    global open_ont_dict
    open_ont_dict[ontology_key] = {
        "ranges_dict": ranges_dict,
        "subclass_dict": subclass_dict,
        "sameas_dict": sameas_dict,
    }
    return open_ont_dict


def config_open_onts():
    global open_ont_dict
    add_open_ont(
        "acl",
        ranges_dict={
            "AuthenticatedAgent": [
                "coordinateQualityCheckPerformedBy",
                "createUser",
                "modifyUser",
                "preloadFileCreateUser",
                "preloadFileModifyUser",
            ]
        },
        subclass_dict={},
        sameas_dict={},
    )

    add_open_ont(
        "time",
        ranges_dict={
            "DateTimeDescription": [
                "acquisitionDate",
                "activityStartDateTime",
                "activityStopDateTime",
                "analysisDate",
                "commentTime",
                "commitDate",
                "coordinateQualityCheckDateTime",
                "coreRecoveredDate",
                "coringOperationDate",
                "createTime",
                "creationDateTime",
                "cutDate",
                "dataRuleCreatedOn",
                "dataRulePublishedOn",
                "dataRuleUpdatedOn",
                "date",
                "dateModified",
                "datePublished",
                "dateStamp",
                "dateTime",
                "daylightSavingTimeEndDate",
                "daylightSavingTimeStartDate",
                "deadline",
                "drillingStartDateTime",
                "drillingStopDateTime",
                "effectiveDate",
                "effectiveDateTime",
                "endDate",
                "endDateActivity",
                "endDateTime",
                "facilitySpecificationDateTime",
                "importTimeStamp",
                "intervalDateTime",
                "issueDateTime",
                "jobEndDateTime",
                "jobStartDateTime",
                "lastAbandonDrillDate",
                "lastBopDrillDate",
                "lastBopPressureTestDate",
                "lastCasingPressureTestDate",
                "lastDiverterDrillDate",
                "lastFireBoatDrillDate",
                "lastRigInspectionDate",
                "lastSafetyInspectionDate",
                "lastSafetyMeetingDate",
                "lastSuccessfulRunDateUTC",
                "lastTripDrillDate",
                "markerDate",
                "modifyTime",
                "nextBopPresTestDate",
                "parameterTypeDefaultValueDateTime",
                "parameterTypeDefaultValueTime",
                "plannedEndTime",
                "plannedStartTime",
                "preloadFileCreateDate",
                "preloadFileModifyDate",
                "projectBeginDate",
                "projectEndDate",
                "projectSpecificationDateTime",
                "publicationDate",
                "recordDate",
                "referenceLogDate",
                "revisionDate",
                "runDateTime",
                "sampleAcquiredDate",
                "sampleDateTime",
                "spatialLocationCoordinatesDate",
                "specificationDate",
                "specificationDateTime",
                "specificationTime",
                "startDate",
                "startDateActivity",
                "startDateTime",
                "startTime",
                "statusDateTime",
                "surfacePressureFinalDateTime",
                "terminationDate",
                "terminationDateTime",
                "timeValues",
                "totalTime",
                "uTCDateTimeValues",
                "updateDate",
                "validationDate",
                "zeroTime",
            ],
            "TemporalDuration": [
                "bitRunTIme",
                "elapsedTimeCirc",
                "elapsedTimeDrill",
                "elapsedTimeDrillRot",
                "elapsedTimeDrillSlid",
                "elapsedTimeHold",
                "elapsedTimeLoc",
                "elapsedTimeReam",
                "elapsedTimeSpud",
                "elapsedTimeStart",
                "elapsedTimeSteering",
                "maximumAge",
                "minimumAge",
                "nonProductiveTimeDuration",
                "productiveTimeDuration",
                "satelliteRevisitTime",
                "timeReaming",
                "testTimeDuration",
                "timeCirculating",
                "timeDrillingRotating",
                "timeDrillingSliding",
                "timeHolding",
                "timeSteering",
                "validationDuration",
                "wavePeriod",
            ],
        },
        subclass_dict={},
        sameas_dict={},
    )

    add_open_ont(
        ontology_key="foaf",
        ranges_dict={},
        subclass_dict={
            "Image": [
                "GenericImage",
                "GeoReferencedImage",
                "GeoTIFF",
                "JPEG",
                "PNG",
                "TIFF",
            ],
            "Person": ["Personnel"],
        },
        sameas_dict={
            "Organization": ["Organisation"],
            "name": ["incidentReporterName", "interpreterName", "name", "personName"],
        },
    )

    add_open_ont(
        ontology_key="gn",
        ranges_dict={
            "Feature": [
                "boundingBoxEastBoundLongitude",
                "boundingBoxWestBoundLongitude",
                "boundingBoxNorthBoundLatitude",
                "boundingBoxSouthBoundLatitude",
                "otherRelevantDataCountries",
            ]
        },
        subclass_dict={},
        sameas_dict={
            "longitude": [
                "boundingBoxEastBoundLongitude",
                "boundingBoxWestBoundLongitude",
            ],
            "latitude": [
                "boundingBoxNorthBoundLatitude",
                "boundingBoxSouthBoundLatitude",
            ],
            "countryCode": ["otherRelevantDataCountries"],
        },
    )
    return open_ont_dict
