package delivery;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.http.javadsl.Http;
import akka.http.javadsl.ServerBinding;
import akka.http.javadsl.server.Route;
import akka.actor.typed.javadsl.Behaviors;
import akka.actor.typed.ActorSystem;

import java.io.File;
import java.io.FileNotFoundException;
import java.net.InetSocketAddress;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Scanner;
import java.util.concurrent.CompletionStage;

public class Main {

    // #start-http-server
    static void startHttpServer(Route route, ActorSystem<?> system) {
        CompletionStage<ServerBinding> futureBinding =
            Http.get(system).newServerAt("localhost", 8081).bind(route);

        futureBinding.whenComplete((binding, exception) -> {
            if (binding != null) {
                InetSocketAddress address = binding.localAddress();
                system.log().info("Server online at http://{}:{}/",
                    address.getHostString(),
                    address.getPort());
            } else {
                system.log().error("Failed to bind HTTP endpoint, terminating system", exception);
                system.terminate();
            }
        });
    }

    public static Behavior<Void> create(String filename) throws FileNotFoundException{
        return Behaviors.setup(context -> {
            // create a delivery actor
            // for each agent in the initialData.txt
            // spawn agent actor

            HashMap<Integer, HashMap<Integer,Integer>> restData = new HashMap<>();
            ArrayList <Integer> agentIds = new ArrayList<>();

            File initialData = new File(filename);
            Scanner myReader = new Scanner(initialData);
            int count = 3;
            while (count>1 && myReader.hasNextLine()) {
                String currentLine = myReader.nextLine().trim();
                if(currentLine.equals("****")) {
                    --count;
                }
                // restaurant section
                else if (count == 3) {
                    String [] line = currentLine.split(" ");

                    Integer restId = Integer.parseInt(line[0]);
                    int itemCount = Integer.parseInt(line[1]);

                    // adding restaurant id into hashmap
                    restData.put(restId, new HashMap<>());
                    // item details section
                    while(itemCount-- > 0) {
                        currentLine = myReader.nextLine().trim();
                        line = currentLine.split(" ");

                        Integer itemId = Integer.parseInt(line[0]);
                        Integer price = Integer.parseInt(line[1]);

                        // adding items of corresponding restaurant into hashmap
                        restData.get(restId).put(itemId, price);
                    }
                }
                // agentId section
                else if (count == 2) {
                    int agentId = Integer.parseInt(currentLine);
                    agentIds.add(agentId);
                }
            }
            myReader.close();

            ActorRef<Delivery.Command> DeliveryActor = context.spawn(Delivery.create(agentIds, restData), "delivery");

            // linking the userRoutes with the httpServer
            DeliveryRoutes routes = new DeliveryRoutes(context.getSystem(), DeliveryActor);
            startHttpServer(routes.deliveryRoutes(), context.getSystem());

            return Behaviors.empty();
        });
    }
    public static void main(String[] args) throws Exception {
        String filename = "initialData.txt";
        if(args.length != 0) filename = args[0];
        ActorSystem.create(Main.create(filename), "DeliveryService");
    }

}


