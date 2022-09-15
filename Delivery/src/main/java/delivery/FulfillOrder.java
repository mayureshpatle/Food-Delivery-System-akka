package delivery;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;


import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Objects;

public class FulfillOrder extends AbstractBehavior<FulfillOrder.Command> {

    // to send reply to /order/num
    public final static class OrderInfo {
        public int orderId;
        public String status;
        public int agentId;

        OrderInfo(int orderId) {
            this.orderId = orderId;
            this.status = "unassigned";
            this.agentId = -1;
        }
        OrderInfo(int orderId, String status, int agentId){
            this.orderId = orderId;
            this.status = status;
            this.agentId = agentId;
        }
    }


    interface Command {}

    public final static class OrderStatus implements Command{
        int orderId;
        ActorRef<OrderInfo> replyTo;
        public OrderStatus(int orderId, ActorRef<OrderInfo> replyTo){
            this.orderId = orderId;
            this.replyTo = replyTo;
        }
    }

    public final static class RequestOrder implements Command{
        Delivery.Order order;
        public RequestOrder(Delivery.Order order){
            this.order = order;
        }
    }

    public final static class OrderDelivered implements Command {

    }

    public final static class ContactAgent implements Command {
        int agentId;

        public ContactAgent(int agentId) {
            this.agentId = agentId;
        }
    }

    public final static class Assigned implements Command {
        int agentId;
        public Assigned(int agentId) {
            this.agentId = agentId;
        }
    }

    public final static class NotAssigned implements Command {
        int agentId;
        public NotAssigned(int agentId) {
            this.agentId = agentId;
        }
    }

    int orderId;
    HashMap<Integer, ActorRef<Agent.Command>> agentRefs;
    HashMap<Integer, HashMap<Integer,Integer>> restData;
    String status;
    int agentId;
    ActorRef<Delivery.Command> replyTo;
    ArrayList<Integer> agents;
    int idx;

    public static Behavior<Command> create(int orderId, HashMap<Integer, ActorRef<Agent.Command>> agentRefs,
                                           HashMap<Integer, HashMap<Integer,Integer>> restData,
                                           ActorRef<Delivery.Command> replyTo){
        return Behaviors.setup(context -> new FulfillOrder(context, orderId, agentRefs, restData, replyTo));
    }

    public FulfillOrder(ActorContext<Command> context,
                        int orderId,
                        HashMap<Integer, ActorRef<Agent.Command>> agentRefs,
                        HashMap<Integer, HashMap<Integer,Integer>> restData,
                        ActorRef<Delivery.Command> replyTo){
        super(context);
        this.orderId = orderId;
        this.agentRefs = agentRefs;
        this.restData = restData;
        this.replyTo = replyTo;
        this.status = "unassigned";
        this.agentId = -1;
        this.agents = new ArrayList<>(agentRefs.keySet());
        Collections.sort(this.agents);
        this.idx = 0;
    }

    @Override
    public Receive<Command> createReceive(){
        return newReceiveBuilder()
                .onMessage(OrderStatus.class, this::onOrderStatus)
                .onMessage(RequestOrder.class, this::onRequestOrder)
                .onMessage(OrderDelivered.class, this::onOrderDelivered)
                .onMessage(ContactAgent.class, this::onContactAgent)
                .onMessage(Assigned.class, this::onAssigned)
                .onMessage(NotAssigned.class, this::onNotAssigned)
                .build();
    }


    private int httpRequest(String url, String payload) throws IOException, InterruptedException{

        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest
                .newBuilder(URI.create(url))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(payload))
                .build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
//        getContext().getLog().info("{{} => status = {}",url, response.statusCode());
        return response.statusCode();
    }

    private Behavior<Command> onRequestOrder(RequestOrder x) throws IOException, InterruptedException{
        // amount to be deducted from the customer's wallet
        // for the item he ordered
        int amount = restData.get(x.order.restId).get(x.order.itemId) * x.order.qty;

        // uri's to be used
        String url1 = "http://localhost:8080/acceptOrder";
        String url2 = "http://localhost:8082/deductBalance";
        String url3 = "http://localhost:8082/addBalance";

        // payload for restaurant
        String payload1 = String
                .format("{%s:%d,%s:%d,%s:%d}","\"restId\"",x.order.restId,"\"itemId\"",x.order.itemId,"\"qty\"",x.order.qty);

        // payload for wallet
        String payload2 = String
                .format("{%s:%d,%s:%d}","\"custId\"",x.order.custId,"\"amount\"",amount);


        // deduct balance from wallet
        int status = httpRequest(url2, payload2);

        // if wallet has sufficient balance
        if(status == 201){

            // remove the items from restaurant
            // if restaurant has insufficient items
            if(httpRequest(url1, payload1) == 410){

                // add the deducted balance to the wallet
                httpRequest(url3, payload2);

                // mark status as rejected
                this.status = "rejected";
                return this;
            }
        }
        else {      // insufficient balance
            // mark status as rejected
            this.status = "rejected";
            return this;
        }

        agentRefs.get(agents.get(idx++)).tell(new Agent.ChangeStatus("unavailable", getContext().getSelf(),1));

        return this;
    }
    private Behavior<Command> onOrderStatus(OrderStatus x){
        // tell client the status of the order
        x.replyTo.tell(new OrderInfo(x.orderId, this.status, this.agentId));
        return this;
    }

    private Behavior<Command> onOrderDelivered(OrderDelivered x) {
        // if order is not in assigned state
        if (!Objects.equals(status, "assigned")) return this;
        this.status = "delivered";

        // tell the agent that they are available
        this.agentRefs.get(agentId).tell(new Agent.ChangeStatus("available", getContext().getSelf(), 1));
        return this;
    }

    private Behavior<Command> onContactAgent(ContactAgent x) {
        agentRefs.get(x.agentId).tell(new Agent.ChangeStatus("unavailable", getContext().getSelf(),1));
        return this;
    }

    private Behavior<Command> onAssigned(Assigned x){
        // update status and agentId
        this.agentId = x.agentId;
        this.status = "assigned";
        return this;
    }

    private Behavior<Command> onNotAssigned(NotAssigned x){
        if(this.idx < agents.size()) {
            // contact next agent
            agentRefs.get(agents.get(idx++)).tell(new Agent.ChangeStatus("unavailable", getContext().getSelf(),1));
        }
        else {
            // tell delivery that order is waiting to be assigned
            this.replyTo.tell(new Delivery.WaitingOrder(this.orderId));
        }
        return this;
    }
}
