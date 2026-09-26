package shop;

import java.util.ArrayList;
import java.util.List;

/** Replays a lookup-heavy workload: java -cp out shop.Replay */
public final class Replay {
    public static void main(String[] args) {
        String[] tenants = new String[500];
        for (int t = 0; t < tenants.length; t++) {
            tenants[t] = "tenant-" + t;
        }
        List<Order> orders = new ArrayList<>();
        for (int i = 0; i < 200_000; i++) {
            orders.add(new Order(tenants[i % 500], i, i * 31L));
        }
        OrderIndex index = new OrderIndex(orders);
        long sum = 0;
        long start = System.nanoTime();
        for (int round = 0; round < 50; round++) {
            for (int i = 0; i < 200_000; i++) {
                Order o = index.find(tenants[i % 500], i);
                if (o != null) {
                    sum += o.cents();
                }
            }
        }
        System.out.printf("sum=%d elapsed=%d ms%n", sum, (System.nanoTime() - start) / 1_000_000);
    }
}
