package jhu.wikilinks;

import redis.clients.jedis.Jedis;

class JedisTest {
    public static void main(String[] args) {
        String host = "localhost";
        String dump_dir  = System.getProperty("user.dir");
        String dump_file = "test.rdb";
        Jedis jedis = new Jedis("localhost");
        jedis.configSet("dir", dump_dir);
        jedis.configSet("dbfilename", dump_file);
        jedis.set("test_key", "test_value");
        System.out.println("ret = " + jedis.get("test_key"));
        String status = jedis.save();
        if(!status.equals("OK")) {
            System.err.println("Problem saving redis dump; status = " + status);
            System.exit(1);
        }
    }
}
