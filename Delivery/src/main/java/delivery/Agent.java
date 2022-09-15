package delivery;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.*;

import java.util.Objects;

public class Agent extends AbstractBehavior<Agent.Command> {
    // to send reply to /agent/num
    public final static class AgentInfo{
        public int agentId;
        public String status;
        public AgentInfo(int agentId, String status){
            this.agentId = agentId;
            this.status = status;
        }
    }

    interface Command {}

    public final static class AgentStatus implements Command{
        ActorRef<Agent.AgentInfo> replyTo;
        int agentId;
        public AgentStatus(int agentId, ActorRef<Agent.AgentInfo> replyTo){
            this.agentId = agentId;
            this.replyTo = replyTo;
        }
    }

    public final static class ChangeStatus implements Command{
        String newStatus;
        ActorRef<FulfillOrder.Command> replyTo;
        int flag;
        // flag == 1 => fulFillOrder
        // flag == 0 => Delivery

        public ChangeStatus(String newStatus, ActorRef<FulfillOrder.Command> replyTo, int flag){
            this.newStatus = newStatus;
            this.replyTo = replyTo;
            this.flag = flag;
        }
    }

    public final static class ForceSignOut implements Command {}

    int agentId;
    String status;

    ActorRef<Delivery.Command> deliveryRef;

    public static Behavior<Command> create(int agentId, ActorRef<Delivery.Command> deliveryRef){
        return Behaviors.setup(context -> new Agent(context, agentId, deliveryRef));
    }
    public Agent(ActorContext<Command> context, int agentId, ActorRef<Delivery.Command> deliveryRef){
        super(context);
        this.agentId = agentId;
        this.status = "signed-out";
        this.deliveryRef = deliveryRef;
        getContext().getLog().info("Agent-{} actor created", this.agentId);
    }

    @Override
    public Receive<Command> createReceive(){
        return newReceiveBuilder()
                .onMessage(AgentStatus.class, this::onAgentStatus)
                .onMessage(ChangeStatus.class, this::onChangeStatus)
                .onMessage(ForceSignOut.class, this::onForceSignOut)
                .build();
    }

    private Behavior<Command> onAgentStatus(AgentStatus x){
        x.replyTo.tell(new AgentInfo(this.agentId, this.status));
        return this;
    }

    private Behavior<Command> onChangeStatus(ChangeStatus x){
        if(x.flag == 0){        // from Delivery

            // sign-out request
            if(Objects.equals(x.newStatus, "signed-out")){
                if(Objects.equals(this.status, "available")) this.status = x.newStatus;
            }

            // sign-in request
            else if(Objects.equals(x.newStatus, "available")){
                if(Objects.equals(this.status, "signed-out")) {
                    this.status = x.newStatus;
                    this.deliveryRef.tell(new Delivery.AgentAvailable(this.agentId));
                }
            }
        }
        else{                   // from FulfillOrder

            // assign request, set unavailable
            if(Objects.equals(x.newStatus, "unavailable")) {
                if(Objects.equals(this.status, "available")) {
                    this.status = x.newStatus;
                    x.replyTo.tell(new FulfillOrder.Assigned(this.agentId));
                }
                else {
                    x.replyTo.tell(new FulfillOrder.NotAssigned(this.agentId));
                }
            }

            // order delivered, set available
            else {
                this.status = x.newStatus;

                // notify delivery about availability of this agent
                this.deliveryRef.tell(new Delivery.AgentAvailable(this.agentId));
            }
        }
        return this;
    }

    private Behavior<Command> onForceSignOut (ForceSignOut x){
        this.status = "signed-out";
        return this;
    }
}
