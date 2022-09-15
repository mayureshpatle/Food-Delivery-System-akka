package Phase1.wallet;

import java.io.File;
import java.util.HashMap;
import java.util.Scanner;
import java.io.FileNotFoundException;
import java.util.concurrent.atomic.AtomicInteger;

// WalletRecord class manages the
// balance of each customer's wallet
public class WalletRecord {

    // Wallet is the hashmap of <custId, balance>
    HashMap <Long, Long> Wallet;
    static HashMap <Long, AtomicInteger> lock = new HashMap<>();
    // constructor
    public WalletRecord() {
        Wallet = new HashMap<>();
        this.Initialize();
    }

    // Initialize the 'Wallet' data from the
    // initialData.txt file
    public void Initialize() {
        try {
            String inputFile = "initialData.txt";
            File initialData = new File(inputFile);
            Scanner myReader = new Scanner(initialData);
            int count = 3;
            while (myReader.hasNextLine()) {
                String currentLine = myReader.nextLine().trim();
                if(currentLine.equals("****")) {
                    --count;
                }
                else if (count == 0) {
                    if(!Wallet.isEmpty()) {
                        long amount = Integer.parseInt(currentLine);
                        Wallet.replaceAll((K, V) -> amount);
                    }
                }
                else if (count == 1) {
                    long custId = Integer.parseInt(currentLine);
                    Wallet.put(custId, 0L);
                    if(WalletRecord.lock.get(custId) == null) {
                        WalletRecord.lock.put(custId, new AtomicInteger(0));
                    }
                }
            }
            myReader.close();
        } catch (FileNotFoundException e) {
            System.out.println("Initializer File Not Found.");
            e.printStackTrace();
        }
    }

    // addBalance function increments the custId's balance by 'amount'
    public void addBalance(long custId, long amount) {
        long curr_amount = this.Wallet.get(custId);
        this.Wallet.replace(custId, curr_amount + amount);
    }

    // deductBalance function decrements the custId's balance by 'amount'
    // if the current balance of custId is greater than or equal to 'amount'
    // and returns true if balance is successfully deducted
    // otherwise returns false
    public boolean deductBalance(long custId, long amount) {
        long curr_amount = this.Wallet.get(custId);
        if (curr_amount < amount) return false;

        this.Wallet.replace(custId, curr_amount - amount);
        return true;
    }

    // getBalance function returns the current balance
    // of 'custId'
    public long getBalance(long custId){
        return this.Wallet.get(custId);
    }

    public String getString() {
         return this.Wallet.toString();
     }


}