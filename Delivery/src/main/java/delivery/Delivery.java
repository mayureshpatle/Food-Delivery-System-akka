package delivery;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.AbstractBehavior;
import akka.actor.typed.javadsl.ActorContext;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.javadsl.Receive;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class Delivery extends AbstractBehavior<Delivery.Command> {

    // user related classes

    // to send reply to /requestOrder
    public final static class OrderInfo{
        public int orderId;
        OrderInfo(int orderId){
            this.orderId = orderId;
        }
    }

    // to send generic message
    public final static class Done{
        public String msg;
        public Done(String msg){
            this.msg = msg;
        }
    }

    // to receive new order details from client
    // /requestOrder
    public final static class Order{
        public final int custId;
        public final int restId;
        public final int itemId;
        public final int qty;
        @JsonCreator
        public Order(@JsonProperty("custId") int custId,
                     @JsonProperty("restId") int restId,
                     @JsonProperty("itemId") int itemId,
                     @JsonProperty("qty") int qty) {
            this.custId = custId;
            this.restId = restId;
            this.itemId = itemId;
            this.qty = qty;
        }
    }

    // to receive orderId from client
    // /orderDelivered
    public final static class OrderId{
        public final int orderId;
        @JsonCreator
        public OrderId(@JsonProperty("orderId") int orderId){
            this.orderId = orderId;
        }
    }

    // to receive agentId from client
    // /agentSignIn     /agentSignOut
    public final static class AgentId{
        public final int agentId;
        @JsonCreator
        public AgentId(@JsonProperty("agentId") int agentId){
            this.agentId = agentId;
        }
    }

    interface Command {}

    public final static class RequestOrder implements Command {
        public final Order order;
        ActorRef<OrderInfo> replyTo;
        public RequestOrder(Order order, ActorRef<OrderInfo> replyTo) {
            this.order = order;
            this.replyTo = replyTo;
        }
    }


    public final static class ReInitialize implements Command {
        ActorRef<Done> replyTo;
        public ReInitialize(ActorRef<Done> replyTo) {
            this.replyTo = replyTo;
        }
    }

    public final static class OrderStatus implements Command {
        public ActorRef<FulfillOrder.OrderInfo> replyTo;
        public int orderId;
        public OrderStatus(ActorRef<FulfillOrder.OrderInfo> replyTo, int orderId){
            this.replyTo = replyTo;
            this.orderId = orderId;
        }
    }

    public final static class AgentSignIn implements Command{
        public ActorRef<Delivery.Done> replyTo;
        int agentId;
        public AgentSignIn(ActorRef<Delivery.Done> replyTo, AgentId agentId){
            this.replyTo = replyTo;
            this.agentId = agentId.agentId;
        }
    }

    public final static class AgentSignOut implements Command{
        public ActorRef<Delivery.Done> replyTo;
        int agentId;
        public AgentSignOut(ActorRef<Delivery.Done> replyTo, AgentId agentId){
            this.replyTo = replyTo;
            this.agentId = agentId.agentId;
        }
    }

    public final static class AgentStatus implements Command {
        public ActorRef<Agent.AgentInfo> replyTo;
        public int agentId;
        public AgentStatus(ActorRef<Agent.AgentInfo> replyTo, int agentId){
            this.replyTo = replyTo;
            this.agentId = agentId;
        }
    }

    public final static class AgentAvailable implements Command {
        public int agentId;
        public AgentAvailable(int agentId){
            this.agentId = agentId;
        }
    }

    public final static class OrderDelivered implements Command {
        public ActorRef<Delivery.Done> replyTo;
        int orderId;
        public OrderDelivered(ActorRef<Delivery.Done> replyTo, OrderId orderId) {
            this.replyTo = replyTo;
            this.orderId = orderId.orderId;
        }
    }

    public final static class WaitingOrder implements Command {
        int orderId;
        public WaitingOrder(int orderId){
            this.orderId = orderId;
        }
    }


    HashMap<Integer, ActorRef<FulfillOrder.Command>> orderRefs;
    HashMap<Integer, ActorRef<Agent.Command>> agentRefs;
    HashMap<Integer, HashMap<Integer,Integer>> restData;
    Integer orderId;
    PriorityQueue<Integer> orderQueue;

    public static Behavior<Command> create(ArrayList<Integer> agentIds, HashMap<Integer, HashMap<Integer,Integer>> restData){
        return Behaviors.setup(context -> new Delivery(context, agentIds, restData));
    }
    public Delivery(ActorContext<Command> context, ArrayList <Integer> agentIds, HashMap<Integer, HashMap<Integer,Integer>> restData) throws UnsupportedEncodingException {
        super(context);

        // SpawnAgents
        this.agentRefs = new HashMap<>();
        for (int agentId : agentIds) {
            ActorRef<Agent.Command> agentRef = getContext().spawn(Agent.create(agentId, getContext().getSelf()),
                    URLEncoder.encode("agent " + agentId, StandardCharsets.UTF_8.name()));
            this.agentRefs.put(agentId, agentRef);
        }
        this.restData = restData;
        this.orderId = 999;
        this.orderRefs = new HashMap<>();
        this.orderQueue = new PriorityQueue<>();
//        getContext().getLog().info("size of agentRefs = {}, size of restData = {}", agentRefs.size(), restData.size());
    }

    @Override
    public Receive<Command> createReceive(){
        return newReceiveBuilder()
                .onMessage(ReInitialize.class, this::onReInitialize)
                .onMessage(RequestOrder.class, this::onRequestOrder)
                .onMessage(OrderStatus.class, this::onOrderStatus)
                .onMessage(AgentStatus.class, this::onAgentStatus)
                .onMessage(AgentSignOut.class, this::onAgentSignOut)
                .onMessage(AgentSignIn.class, this::onAgentSignIn)
                .onMessage(OrderDelivered.class, this::onOrderDelivered)
                .onMessage(AgentAvailable.class, this::onAgentAvailable)
                .onMessage(WaitingOrder.class, this::onWaitingOrder)
                .build();
    }

    private Behavior<Command> onReInitialize(ReInitialize x) throws UnsupportedEncodingException {
        // stop all the spawned FulFillOrder Actors
        orderRefs.forEach((K, V) -> getContext().stop(V));
        orderRefs = new HashMap<>();

        // tell all Agent Actors to sign out
        agentRefs.forEach((K, agentRef) -> agentRef.tell(new Agent.ForceSignOut()));

        // reset orderQueue
        orderQueue = new PriorityQueue<>();

        // reset the orderId
        this.orderId = 999;

        // reply to the client
        x.replyTo.tell(new Done(""));

        return this;
    }

    private Behavior<Command> onRequestOrder(RequestOrder x) throws UnsupportedEncodingException{
        // generate the order id
        this.orderId ++;

        // spawn a FulFillOrder actor
        // pass the list of agent actors and restData to the actor
        ActorRef<FulfillOrder.Command> ref =
                getContext().spawn(FulfillOrder.create(orderId, agentRefs, restData, getContext().getSelf()),
                        URLEncoder.encode("order " + this.orderId, StandardCharsets.UTF_8.name()));

        // keep the ref into orderRefs map
        orderRefs.put(this.orderId, ref);

        ref.tell(new FulfillOrder.RequestOrder(x.order));

        // return the orderId to client
        x.replyTo.tell(new OrderInfo(this.orderId));

        return this;
    }

    private Behavior<Command> onOrderStatus(OrderStatus x){
//        getContext().getLog().info("orderId is {}", x.orderId);

        // if orderId is invalid
        // send 404 response to the client
        if(orderRefs.get(x.orderId) == null)
            x.replyTo.tell(new FulfillOrder.OrderInfo(-1));

        // else tell the corresponding FullFillOrder Actor
        // to send the appropriate response to the client
        else
            orderRefs.get(x.orderId).tell(new FulfillOrder.OrderStatus(x.orderId, x.replyTo));

        return this;
    }

    private Behavior<Command> onAgentStatus(AgentStatus x){
        agentRefs.get(x.agentId).tell(new Agent.AgentStatus(x.agentId, x.replyTo));
        return this;
    }

    private Behavior<Command> onAgentSignOut(AgentSignOut x){
        // tell the agent to sign out
        this.agentRefs.get(x.agentId).tell(new Agent.ChangeStatus("signed-out", null, 0));
        x.replyTo.tell(new Done(""));
        return this;
    }

    private Behavior<Command> onAgentSignIn(AgentSignIn x){
        // try to set status available (if current status is signed-out)
        this.agentRefs.get(x.agentId).tell(new Agent.ChangeStatus("available", null, 0));
        x.replyTo.tell(new Done(""));
        return this;
    }

    private Behavior<Command> onOrderDelivered(OrderDelivered x){
        // try to set status signed-out (if current status is available)
        orderRefs.get(x.orderId).tell(new FulfillOrder.OrderDelivered());
        x.replyTo.tell(new Done(""));
        return this;
    }

    private Behavior<Command> onAgentAvailable(AgentAvailable x){
        // notify one of the waiting FulfillOrder actor (if available) about agent
        if(orderQueue.isEmpty()) return this;
        int order = orderQueue.poll();
        ActorRef<FulfillOrder.Command> orderRef = orderRefs.get(order);
        orderRef.tell(new FulfillOrder.ContactAgent(x.agentId));
        return this;
    }

    private Behavior<Command> onWaitingOrder(WaitingOrder x){
        // add waiting FulfillOrder actor to orderQueue
        orderQueue.add(x.orderId);
        return this;
    }

}
