package Phase1.wallet;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

// PersonalWallet class is to receive
// JSON data from/to the customer
class PersonalWallet {
    public long custId, amount;
}

// PersonalWallet class is to send
// JSON data from/to the customer
class PersonalWallet2 {
    public long custId, balance;
}

@RestController
public class RequestController {

    // WalletInstance keeps track of the
    // balance of each customer's wallet
    WalletRecord WalletInstance;


    // constructor
    public RequestController(){
        WalletInstance = new WalletRecord();
    }
    // POST /addBalance
    @PostMapping("/addBalance")
    public ResponseEntity<String> addBalance(@RequestBody PersonalWallet Query) {
        acquire(WalletRecord.lock.get(Query.custId));
        this.WalletInstance.addBalance(Query.custId, Query.amount);
        release(WalletRecord.lock.get(Query.custId));


        return ResponseEntity.status(201).body("");
    }

    // POST /deductBalance
    @PostMapping("/deductBalance")
    public ResponseEntity<String> deductBalance(@RequestBody PersonalWallet Query) {
        acquire(WalletRecord.lock.get(Query.custId));
        boolean status = this.WalletInstance.deductBalance(Query.custId, Query.amount);
        release(WalletRecord.lock.get(Query.custId));

        if(status) return ResponseEntity.status(201).body("");
        else return ResponseEntity.status(410).body("");
    }

    // GET /balance/num
    @GetMapping("/balance/{custId}")
    public ResponseEntity<PersonalWallet2> getBalance(@PathVariable Long custId) {
        acquire(WalletRecord.lock.get(custId));

        PersonalWallet2 response = new PersonalWallet2();
        response.custId = custId;
        response.balance = this.WalletInstance.getBalance(custId);

        release(WalletRecord.lock.get(custId));

        return ResponseEntity.status(200).body(response);
    }

    // POST /reInitialize
    @PostMapping("/reInitialize")
    public ResponseEntity<String > reInitialize() {
        WalletRecord.lock.forEach((K, V)->acquire(V));
        this.WalletInstance.Initialize();
        WalletRecord.lock.forEach((K, V)->release(V));
        return ResponseEntity.status(201).body("");
    }

//     this endpoint is just for our internal testing
     @GetMapping("/showWallet")
     public String showWallet() {
         return this.WalletInstance.getString();
     }

    void acquire(AtomicInteger x){
        while(!x.compareAndSet(0,1));
    }

    void release(AtomicInteger x){
        x.set(0);
    }
}
