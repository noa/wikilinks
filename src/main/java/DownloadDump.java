package jhu.wikilinks;

import org.wikidata.wdtk.dumpfiles.DumpContentType;
import org.wikidata.wdtk.dumpfiles.DumpProcessingController;
import org.wikidata.wdtk.dumpfiles.EntityTimerProcessor;
import org.wikidata.wdtk.dumpfiles.EntityTimerProcessor.TimeoutException;
import org.wikidata.wdtk.dumpfiles.MwDumpFile;

public class DownloadDump {
    public static final ExampleHelpers.DumpProcessingMode DUMP_FILE_MODE = DumpProcessingMode.JSON;

    public static void main(String[] args) {
        // Controller object for processing dumps:
        DumpProcessingController dumpProcessingController = new DumpProcessingController(
            "wikidatawiki");
        dumpProcessingController.setOfflineMode(OFFLINE_MODE);

        // // Optional: Use another download directory:
        // dumpProcessingController.setDownloadDirectory(System.getProperty("user.dir"));

        // Should we process historic revisions or only current ones?
        boolean onlyCurrentRevisions;
        switch (DUMP_FILE_MODE) {
        case ALL_REVS:
        case ALL_REVS_WITH_DAILIES:
            onlyCurrentRevisions = false;
            break;
        case CURRENT_REVS:
        case CURRENT_REVS_WITH_DAILIES:
        case JSON:
        case JUST_ONE_DAILY_FOR_TEST:
        default:
            onlyCurrentRevisions = true;
        }

        MwDumpFile dumpFile = null;
        try {
            // Start processing (may trigger downloads where needed):
            switch (DUMP_FILE_MODE) {
            case ALL_REVS:
            case CURRENT_REVS:
                dumpFile = dumpProcessingController
                    .getMostRecentDump(DumpContentType.FULL);
                break;
            case ALL_REVS_WITH_DAILIES:
            case CURRENT_REVS_WITH_DAILIES:
                MwDumpFile fullDumpFile = dumpProcessingController
                    .getMostRecentDump(DumpContentType.FULL);
                MwDumpFile incrDumpFile = dumpProcessingController
                    .getMostRecentDump(DumpContentType.DAILY);
                lastDumpFileName = fullDumpFile.getProjectName() + "-"
                    + incrDumpFile.getDateStamp() + "."
                    + fullDumpFile.getDateStamp();
                dumpProcessingController.processAllRecentRevisionDumps();
                break;
            case JSON:
                dumpFile = dumpProcessingController
                    .getMostRecentDump(DumpContentType.JSON);
                break;
            case JUST_ONE_DAILY_FOR_TEST:
                dumpFile = dumpProcessingController
                    .getMostRecentDump(DumpContentType.DAILY);
                break;
            default:
                throw new RuntimeException("Unsupported dump processing type "
                                           + DUMP_FILE_MODE);
            }

            if (dumpFile != null) {
                lastDumpFileName = dumpFile.getProjectName() + "-"
                    + dumpFile.getDateStamp();
                dumpProcessingController.processDump(dumpFile);
            }
        } catch (TimeoutException e) {
            // The timer caused a time out. Continue and finish normally.
        }

        // Print final timer results:
        entityTimerProcessor.close();
    }
}
