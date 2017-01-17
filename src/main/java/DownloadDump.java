package jhu.wikilinks;

import java.io.IOException;

import org.apache.log4j.ConsoleAppender;
import org.apache.log4j.Level;
import org.apache.log4j.Logger;
import org.apache.log4j.PatternLayout;

import org.wikidata.wdtk.dumpfiles.DumpContentType;
import org.wikidata.wdtk.dumpfiles.DumpProcessingController;
import org.wikidata.wdtk.dumpfiles.EntityTimerProcessor;
import org.wikidata.wdtk.dumpfiles.EntityTimerProcessor.TimeoutException;
import org.wikidata.wdtk.dumpfiles.MwDumpFile;
import org.wikidata.wdtk.dumpfiles.wmf.WmfDumpFileManager;

import org.wikidata.wdtk.util.DirectoryManager;
import org.wikidata.wdtk.util.DirectoryManagerFactory;
import org.wikidata.wdtk.util.WebResourceFetcher;
import org.wikidata.wdtk.util.WebResourceFetcherImpl;

import jhu.wikilinks.ExampleHelpers.DumpProcessingMode;

public class DownloadDump {
    /**
     * Timeout to abort processing after a short while or 0 to disable timeout.
     * If set, then the processing will cleanly exit after about this many
     * seconds, as if the dump file would have ended there. This is useful for
     * testing (and in particular better than just aborting the program) since
     * it allows for final processing and proper closing to happen without
     * having to wait for a whole dump file to process.
     */
    public static final int TIMEOUT_SEC = 0;

    public static final DumpProcessingMode DUMP_FILE_MODE = DumpProcessingMode.JSON;

    /**
     * Defines how messages should be logged. This method can be modified to
     * restrict the logging messages that are shown on the console or to change
     * their formatting. See the documentation of Log4J for details on how to do
     * this.
     */
    public static void configureLogging() {
        // Create the appender that will write log messages to the console.
        ConsoleAppender consoleAppender = new ConsoleAppender();
        // Define the pattern of log messages.
        // Insert the string "%c{1}:%L" to also show class name and line.
        String pattern = "%d{yyyy-MM-dd HH:mm:ss} %-5p - %m%n";
        consoleAppender.setLayout(new PatternLayout(pattern));
        // Change to Level.ERROR for fewer messages:
        consoleAppender.setThreshold(Level.INFO);

        consoleAppender.activateOptions();
        Logger.getRootLogger().addAppender(consoleAppender);
    }

    public static void main(String[] args) {
        configureLogging();
        String projectName = "wikidatawiki";
        String downloadDirectory = System.getProperty("user.dir");
        try {
        WebResourceFetcher webResourceFetcher = new WebResourceFetcherImpl();
        DirectoryManager downloadDirectoryManager = DirectoryManagerFactory.createDirectoryManager(downloadDirectory, false);
        WmfDumpFileManager wmfDumpFileManager = new WmfDumpFileManager(projectName, downloadDirectoryManager, webResourceFetcher);
        MwDumpFile result = wmfDumpFileManager
            .findMostRecentDump(DumpContentType.JSON);
            result.prepareDumpFile();
        } catch (IOException e) {
            System.err.println("IO exception");
            System.exit(1);
        }
    }
}
