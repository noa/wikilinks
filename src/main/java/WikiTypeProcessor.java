package jhu.wikilinks;

import java.io.IOException;
import java.io.PrintStream;
import java.util.Set;
import java.util.Map;

import com.google.common.collect.Sets;
import com.google.common.collect.Maps;

import org.wikidata.wdtk.datamodel.interfaces.EntityDocumentProcessor;
import org.wikidata.wdtk.datamodel.interfaces.ItemDocument;
import org.wikidata.wdtk.datamodel.interfaces.PropertyDocument;
import org.wikidata.wdtk.datamodel.interfaces.Statement;
import org.wikidata.wdtk.datamodel.interfaces.StatementGroup;
import org.wikidata.wdtk.datamodel.interfaces.TimeValue;
import org.wikidata.wdtk.datamodel.interfaces.Value;
import org.wikidata.wdtk.datamodel.interfaces.ValueSnak;
import org.wikidata.wdtk.datamodel.interfaces.SiteLink;
import org.wikidata.wdtk.datamodel.interfaces.EntityIdValue;
import org.wikidata.wdtk.datamodel.interfaces.ItemIdValue;

import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.JedisPoolConfig;

// import org.wikidata.wdtk.examples.ExampleHelpers;

/**
 * The HelloWorldApp class implements an application that
 * simply displays "Hello World!" to the standard output.
 */
class WikiTypeProcessor implements EntityDocumentProcessor {
    String wiki;
    //Jedis jedis;
    JedisPool pool;

    public WikiTypeProcessor(String wiki,
                             String redis_host,
                             int redis_port,
                             int redis_timeout,
                             String redis_dump_file) {
        this.wiki = wiki;
        this.pool = new JedisPool(new JedisPoolConfig(),
                                  redis_host,
                                  redis_port,
                                  redis_timeout);
        String redis_dump_dir = System.getProperty("user.dir");
        System.out.println("redis dump dir: " + redis_dump_dir);
        System.out.println("redis dump file: " + redis_dump_file);
        try (Jedis jedis = pool.getResource()) {
            jedis.configSet("dir", redis_dump_dir);
            jedis.configSet("dbfilename", redis_dump_file);
            jedis.flushAll(); // flush previous redis contents
        }
        System.out.println("finished redis configuration");
    }

    /**
     * Main method. Processes the whole dump using this processor and writes the
     * results to a file. To change which dump file to use and whether to run in
     * offline mode, modify the settings in {@link ExampleHelpers}.
     *
     * @param args
     * @throws IOException
     */
    public static void main(String[] args) {
        String wiki = args[0];
        String redis_host = args[1];
        int redis_port = Integer.parseInt(args[2]);
        int redis_timeout = Integer.parseInt(args[3]);
        String redis_dump_file = args[4];
        System.out.println("REDIS HOST " + redis_host + " DUMP " + redis_dump_file);
        ExampleHelpers.configureLogging();
        System.out.println("Initializing WikiTypeProcessing...");
        WikiTypeProcessor processor = new WikiTypeProcessor(wiki,
                                                            redis_host,
                                                            redis_port,
                                                            redis_timeout,
                                                            redis_dump_file);
        System.out.println("Processing entities...");
        ExampleHelpers.processEntitiesFromWikidataDump(processor);
        System.out.println("Writing final results...");
        processor.writeFinalResults();
    }

    @Override
    public void processItemDocument(ItemDocument itemDocument) {
        //String title = itemDocument.getItemId().getId();
        //System.out.println("title = " + title);
        //System.out.println("site = " + itemDocument.getSiteLinks().get(wiki).getPageTitle());
        SiteLink site = itemDocument.getSiteLinks().get(wiki);

        if (site == null) {
            return;
        }
        String title = site.getPageTitle();
        //System.out.println("title = " + title);

        //Map<String, SiteLink> links = itemDocument.getSiteLinks();
        //for(String key : links.keySet()) {
        //    System.out.println("key = " + key);
        //}

        Set<String> types;
        for (StatementGroup statementGroup : itemDocument.getStatementGroups()) {
            switch (statementGroup.getProperty().getId()) {
            case "P31": // instance of
                types = getTypesIfAny(statementGroup);
                try (Jedis jedis = pool.getResource()) {
                    for(String t : types) {
                        //System.out.println("\ttype = " + t);
                        jedis.sadd(title, t);
                    }
                }
                break;
            }
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
        System.out.println("Saving redis state...");
        try (Jedis jedis = pool.getResource()) {
            long now = System.currentTimeMillis() / 1000L;
            System.out.println("now = " + now);
            String status = jedis.bgsave(); // start a background save
            long lastsave = jedis.lastsave();
            while(lastsave < now) {
                System.out.print("last save: " + lastsave);
                System.out.println(" ; waiting for bgsave to complete...");
                try {
                    Thread.sleep(5000); // 5s
                } catch(InterruptedException ex) {
                    Thread.currentThread().interrupt();
                }
                lastsave = jedis.lastsave();
            }
        }
        pool.destroy();
    }

    private Set<String> getTypesIfAny(StatementGroup statementGroup) {
        Set<String> ret = Sets.newHashSet();
        // Iterate over all statements
        for (Statement s : statementGroup.getStatements()) {
            // Find the main claim and check if it has a value
            if (s.getClaim().getMainSnak() instanceof ValueSnak) {
                Value v = ((ValueSnak) s.getClaim().getMainSnak()).getValue();
                //ret.add(v.toString());
                assert( v instanceof EntityIdValue );
                EntityIdValue ev = (EntityIdValue)v;
                ret.add(ev.getId());
            }
        }
        return ret;
    }
}
