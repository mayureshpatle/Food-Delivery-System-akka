package Phase1.restaurant;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

public class resObj {
    // restaurant Id
    int restId;
    // List of items and their quantity
    ArrayList<ArrayList<Integer>> items;
    // synchronization variable
    static HashMap<Integer, AtomicInteger> lock = new HashMap<>();

    // constructor
    resObj(int resId) {
        this.restId = resId;
        items = new ArrayList<>();
    }

    // add itemId with qty quantity
    void AddItem(int itemId, int qty) {
        for (ArrayList<Integer> item : items) {
            if (item.get(0) == itemId) {
                item.set(1, item.get(1) + qty);
                break;
            }
        }
    }


    // remove an itemId with qty quantity
    // if possible
    boolean removeItem(int itemId, int qty) {
        boolean status = false;
        for (ArrayList<Integer> item : items) {
            if (item.get(0) == itemId) {
                if (item.get(1) >= qty) {
                    item.set(1, item.get(1) - qty);
                    status = true;
                }
                break;
            }
        }
        return status;
    }

    // Initialize the list of items
    void initialize(ArrayList<ArrayList<Integer>> items) {
        this.items = items;
    }

    public String toString() {
        String s = "restId: " + restId + "<br>";
        for (ArrayList<Integer> item : items) {
            s = s + "itemId: " + item.get(0) + ", qty: " + item.get(1) + " <br>";
        }
        s = s + "---------------------------------------";
        return s;
    }
}
