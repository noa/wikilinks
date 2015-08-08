package jhu.wikilinks;

import java.io.IOException;
import java.io.PrintStream;

import org.wikidata.wdtk.datamodel.interfaces.EntityDocumentProcessor;
import org.wikidata.wdtk.datamodel.interfaces.ItemDocument;
import org.wikidata.wdtk.datamodel.interfaces.PropertyDocument;
import org.wikidata.wdtk.datamodel.interfaces.Statement;
import org.wikidata.wdtk.datamodel.interfaces.StatementGroup;
import org.wikidata.wdtk.datamodel.interfaces.TimeValue;
import org.wikidata.wdtk.datamodel.interfaces.Value;
import org.wikidata.wdtk.datamodel.interfaces.ValueSnak;

// import org.wikidata.wdtk.examples.ExampleHelpers;

/**
 * The HelloWorldApp class implements an application that
 * simply displays "Hello World!" to the standard output.
 */
class WikiTypeProcessor implements EntityDocumentProcessor {
    long totalPeopleCount = 0;
    long totalLifeSpan = 0;
    boolean printedStatus = true;

    // Simply store data indexed by year of birth, in a range from 0 to 2100:
    final long[] lifeSpans = new long[2100];
    final long[] peopleCount = new long[2100];

    /**
     * Main method. Processes the whole dump using this processor and writes the
     * results to a file. To change which dump file to use and whether to run in
     * offline mode, modify the settings in {@link ExampleHelpers}.
     *
     * @param args
     * @throws IOException
     */
    public static void main(String[] args) {
        System.out.println("Hello World!"); // Display the string.
        ExampleHelpers.configureLogging();
        WikiTypeProcessor.printDocumentation();
        WikiTypeProcessor processor = new WikiTypeProcessor();
        ExampleHelpers.processEntitiesFromWikidataDump(processor);
        processor.writeFinalResults();
    }

    @Override
    public void processItemDocument(ItemDocument itemDocument) {
        int birthYear = Integer.MIN_VALUE;
        int deathYear = Integer.MIN_VALUE;

        for (StatementGroup statementGroup : itemDocument.getStatementGroups()) {
            switch (statementGroup.getProperty().getId()) {
            case "P569": // P569 is "birth date"
                birthYear = getYearValueIfAny(statementGroup);
                break;
            case "P570": // P570 is "death date"
                deathYear = getYearValueIfAny(statementGroup);
                break;
            }
        }

        if (birthYear != Integer.MIN_VALUE && deathYear != Integer.MIN_VALUE
            && birthYear >= 1200) {
            // Do some more sanity checks to filter strange values:
            if (deathYear > birthYear && deathYear - birthYear < 130) {
                lifeSpans[birthYear] += (deathYear - birthYear);
                peopleCount[birthYear]++;
                totalLifeSpan += (deathYear - birthYear);
                totalPeopleCount++;
                printedStatus = false;
            }
        }

        // Print the status once in a while:
        if (!printedStatus && totalPeopleCount % 10000 == 0) {
            printStatus();
            printedStatus = true;
        }
    }

    @Override
    public void processPropertyDocument(PropertyDocument propertyDocument) {
        // nothing to do for properties
    }

    /**
     * Writes the results of the processing to a file.
     */
    public void writeFinalResults() {
        printStatus();
        try (PrintStream out = new PrintStream(
                 ExampleHelpers.openExampleFileOuputStream("life-expectancies.csv"))) {
            for (int i = 0; i < lifeSpans.length; i++) {
                if (peopleCount[i] != 0) {
                    out.println(i + "," + (double) lifeSpans[i]
                                / peopleCount[i] + "," + peopleCount[i]);
                }
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    /**
     * Prints some basic documentation about this program.
     */
    public static void printDocumentation() {
        System.out
            .println("********************************************************************");
        System.out.println("*** Wikidata Toolkit: LifeExpectancyProcessor");
        System.out.println("*** ");
        System.out
            .println("*** This program will download and process dumps from Wikidata.");
        System.out
            .println("*** It will compute the average life expectancy of persons found");
        System.out
            .println("*** In the data. Results will be stored in a CSV file.");
        System.out.println("*** See source code for further details.");
        System.out
            .println("********************************************************************");

    }

    /**
     * Prints the current status to the system output.
     */
    private void printStatus() {
        if (this.totalPeopleCount != 0) {
            System.out.println("Found " + totalPeopleCount
                + " people with an average life span of "
                               + (float) totalLifeSpan / totalPeopleCount + " years.");
        } else {
            System.out.println("Found no people yet.");
        }
    }

    /**
     * Helper method that extracts an integer year from the first time value
     * found in a statement of the given statement group. It checks if the
     * statement has a {@link TimeValue} but also if this value has sufficient
     * precision to extract an exact year.
     *
     * @param statementGroup
     *            the {@link StatementGroup} to extract the year from
     * @return the year, or Interger.MIN_VALUE if none was found
     */
    private int getYearValueIfAny(StatementGroup statementGroup) {
        // Iterate over all statements
        for (Statement s : statementGroup.getStatements()) {
            // Find the main claim and check if it has a value
            if (s.getClaim().getMainSnak() instanceof ValueSnak) {
                Value v = ((ValueSnak) s.getClaim().getMainSnak()).getValue();
                // Check if the value is a TimeValue of sufficient precision
                if (v instanceof TimeValue
                    && ((TimeValue) v).getPrecision() >= TimeValue.PREC_YEAR) {
                    return (int) ((TimeValue) v).getYear();
                }
            }
        }
        return Integer.MIN_VALUE;
    }
}
