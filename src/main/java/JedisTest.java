package jhu.wikilinks;

import redis.clients.jedis.Jedis;

public static void main(String[] args) {
    Jedis jedis = new Jedis("localhost");
    jedis.configSet("dbfilename", "test.rdb");
    jedis.set("test_key", "test_value");
    System.out.println("ret = " + jedis.get("test_key"));
    jedis.save();
}
