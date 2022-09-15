package delivery;

import java.time.Duration;
import java.util.concurrent.CompletionStage;

import akka.actor.typed.ActorRef;
import akka.actor.typed.ActorSystem;
import akka.actor.typed.Scheduler;
import akka.actor.typed.javadsl.AskPattern;
import akka.http.javadsl.marshallers.jackson.Jackson;

import static akka.http.javadsl.server.Directives.*;

import akka.http.javadsl.model.StatusCodes;
import akka.http.javadsl.server.PathMatchers;
import akka.http.javadsl.server.Route;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

//#user-routes-class
public class DeliveryRoutes {
  //#user-routes-class
  private final static Logger log = LoggerFactory.getLogger(DeliveryRoutes.class);
  private final ActorRef<Delivery.Command> DeliveryActor;
  private final Duration askTimeout;
  private final Scheduler scheduler;

  public DeliveryRoutes(ActorSystem<?> system, ActorRef<Delivery.Command> DeliveryActor) {
      this.DeliveryActor = DeliveryActor;
      scheduler = system.scheduler();
      askTimeout = system.settings().config().getDuration("my-app.routes.ask-timeout");
  }

  // /requestOrder
  private CompletionStage<Delivery.OrderInfo> requestOrder(Delivery.Order order){
      return AskPattern.ask(DeliveryActor, ref -> new Delivery.RequestOrder(order, ref), askTimeout, scheduler);
  }
  // /reInitialize
  private CompletionStage<Delivery.Done> reInitialize(){
      return AskPattern.ask(DeliveryActor, Delivery.ReInitialize::new, askTimeout, scheduler);
  }
  // /orderStatus
  private CompletionStage<FulfillOrder.OrderInfo> orderStatus(Integer orderId){
      return AskPattern.ask(DeliveryActor, ref -> new Delivery.OrderStatus(ref, orderId), askTimeout, scheduler);
  }

  // /agentStatus
  private CompletionStage<Agent.AgentInfo> agentStatus(Integer agentId){
      return AskPattern.ask(DeliveryActor, ref -> new Delivery.AgentStatus(ref, agentId), askTimeout, scheduler);
  }

  // /agentSignOut
  private CompletionStage<Delivery.Done> agentSignOut(Delivery.AgentId agentId){
      return AskPattern.ask(DeliveryActor, ref -> new Delivery.AgentSignOut(ref, agentId), askTimeout, scheduler);
  }

  // to be fixed
  // /agentSignIn
  private CompletionStage<Delivery.Done> agentSignIn(Delivery.AgentId agentId){
      return AskPattern.ask(DeliveryActor, ref -> new Delivery.AgentSignIn(ref, agentId), askTimeout, scheduler);
  }

  // to be fixed
  // /orderDelivered
  private CompletionStage<Delivery.Done> orderDelivered(Delivery.OrderId orderId){
      return AskPattern.ask(DeliveryActor, ref -> new Delivery.OrderDelivered(ref, orderId), askTimeout, scheduler);
  }




  public Route deliveryRoutes(){
      return concat(
              // POST /requestOrder
              post(() ->
                      path("requestOrder", () ->
                              entity(Jackson.unmarshaller(Delivery.Order.class), order ->
                                      onSuccess(requestOrder(order), orderInfo ->
                                      {
//                                          log.info("request order : {}", orderInfo.orderId);
                                          return complete(StatusCodes.CREATED, orderInfo, Jackson.marshaller());
                                      })))),

              // POST /reInitialize
              post(() ->
                      path("reInitialize", () ->
                              onSuccess(reInitialize(), (temp) ->
                                      complete(StatusCodes.CREATED)
                              ))),

              // GET /order/num
              get(() ->
                      pathPrefix("order", () ->
                              path(PathMatchers.integerSegment(), (orderId) ->
                                      onSuccess(orderStatus(orderId), orderInfo -> {
                                          if(orderInfo.orderId == -1) return complete(StatusCodes.NOT_FOUND);
                                          return complete(StatusCodes.OK, orderInfo, Jackson.marshaller());
                                      })))),

              // GET /agent/num
              get(() ->
                      pathPrefix("agent", () ->
                              path(PathMatchers.integerSegment(), (agentId) ->
                                      onSuccess(agentStatus(agentId), agentInfo ->
                                           complete(StatusCodes.OK, agentInfo, Jackson.marshaller())
                                      )))),

              // POST /agentSignOut
              post(() ->
                      path("agentSignOut", () ->
                              entity(Jackson.unmarshaller(Delivery.AgentId.class), agentId ->
                                      onSuccess(agentSignOut(agentId), temp ->
                                            complete(StatusCodes.CREATED, temp, Jackson.marshaller())
                                      )))),

              // POST /agentSignIn
              post(() ->
                      path("agentSignIn", () ->
                              entity(Jackson.unmarshaller(Delivery.AgentId.class), agentId ->
                                      onSuccess(agentSignIn(agentId), temp ->
                                              complete(StatusCodes.CREATED, temp, Jackson.marshaller())
                                      )))),

              // POST /orderDelivered
              post(() ->
                      path("orderDelivered", () ->
                              entity(Jackson.unmarshaller(Delivery.OrderId.class), orderId ->
                                      onSuccess(orderDelivered(orderId), temp ->
                                              complete(StatusCodes.CREATED, temp, Jackson.marshaller())
                                      ))))
              );
  }
}
