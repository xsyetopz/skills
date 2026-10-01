package shop;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Read-only lookup of orders by tenant and id, built once at startup. */
public final class OrderIndex {
    private final Map<String, Order> index;

    public OrderIndex(List<Order> orders) {
        index = new HashMap<>(orders.size());
        for (Order o : orders) {
            index.put(o.tenant() + ":" + o.id(), o);
        }
    }

    /** Returns the order, or null when there is none. A later duplicate replaces an earlier one. */
    public Order find(String tenant, int id) {
        return index.get(tenant + ":" + id);
    }

    public int size() {
        return index.size();
    }
}
