package Phase1.restaurant;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.PostMapping;

import java.io.File;
import java.util.Scanner;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.concurrent.atomic.AtomicInteger;

@RestController
public class RestaurantController {

    // R is a hashmap of Restaurant Objects(resObj)
    // R has restaurant id as its key

    HashMap<Integer, resObj> R;

    // Constructor
    RestaurantController() {
        readFileAndInitialize();
    }

    // Read restaurant information from initialData.txt
    // and store the information accordingly in R
    void readFileAndInitialize() {
        R = new HashMap<>();
        try {
            Scanner sc = new Scanner(new File("./initialData.txt"));
            while (sc.hasNextInt()) {
                int resId = sc.nextInt();
                int n = sc.nextInt();
                ArrayList<ArrayList<Integer>> tmp = new ArrayList<>();
                while (n > 0) {
                    ArrayList<Integer> tmp1 = new ArrayList<>();
                    tmp1.add(sc.nextInt()); // adding itemId
                    sc.nextInt();           // excluding price
                    tmp1.add(sc.nextInt()); // adding initial quantity
                    tmp.add(tmp1);
                    n--;
                }
                resObj newRestaurant = new resObj(resId);
                newRestaurant.initialize(tmp);
                R.put(resId, newRestaurant);
                if(resObj.lock.get(resId) == null){
                    resObj.lock.put(resId, new AtomicInteger(0));
                }
            }

        } catch (Exception ex) {
            System.out.println(ex);
        }
    }

    // POST /acceptOrder
    @PostMapping("/acceptOrder")
    public ResponseEntity<String> acceptOrder(@RequestBody Order A) {
        acquire(resObj.lock.get(A.restId));
        boolean status = R.get(A.restId).removeItem(A.itemId, A.qty);
        release(resObj.lock.get(A.restId));

        if (status) return ResponseEntity.status(201).body("");
        else return ResponseEntity.status(410).body("");
    }

    // POST /refillItem
    @PostMapping("/refillItem")
    public ResponseEntity<String> refillItem(@RequestBody Order A) {
        acquire(resObj.lock.get(A.restId));
        R.get(A.restId).AddItem(A.itemId, A.qty);
        release(resObj.lock.get(A.restId));


        return ResponseEntity.status(201).body("");
    }


    // POST /reinitialize
    @PostMapping("/reInitialize")

    public ResponseEntity<String> reInitialize() {
        resObj.lock.forEach((K, V)->acquire(V));
        readFileAndInitialize();
        resObj.lock.forEach((K, V)->release(V));

        return ResponseEntity.status(201).body("");
    }
    

//     This endpoint is just for our internal testing
    @GetMapping("/showRestData")
     public ResponseEntity<String> showRestData() {
         String ans = "";
         for(int restId: R.keySet()) {
             ans += R.get(restId).toString() + "<br>";
         }
         return ResponseEntity.status(200).body(ans);
     }

     void acquire(AtomicInteger x){
        while(!x.compareAndSet(0,1));
     }

     void release(AtomicInteger x){
        x.set(0);
     }
}