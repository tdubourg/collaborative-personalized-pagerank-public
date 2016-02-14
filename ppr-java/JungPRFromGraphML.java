import edu.uci.ics.jung.algorithms.scoring.PageRank;
import edu.uci.ics.jung.graph.DirectedSparseGraph;
import edu.uci.ics.jung.graph.Graph;
import edu.uci.ics.jung.graph.UndirectedSparseGraph;
import edu.uci.ics.jung.io.GraphIOException;
import edu.uci.ics.jung.io.graphml.*;
import org.apache.commons.collections15.Transformer;

import java.io.*;
import java.util.HashMap;
import java.util.Map;

/**
 * Created by troll on 4/18/14.
 */
public class JungPRFromGraphML {
    private static Graph<Integer, Integer> g;

    public static void main(String[] args) {
        System.out.println("Starting loading...");
        long t0 = System.nanoTime();
        load("/home/troll/Copy/collaborative-ppr/my_graph80k.xml");
        long t1 = System.nanoTime();
        System.out.println("Done in" + (t1-t0)/1000000000.0);
        try {
            compute();
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    static int nodes = 0;
    static int edges = 0;
    static void load(String fname) {
        try {
            BufferedReader fileReader = new BufferedReader(new FileReader(fname));
            /* Create the Graph Transformer */
            Transformer<GraphMetadata, Graph<Integer, Integer>>
                    graphTransformer = new Transformer<GraphMetadata,
                    Graph<Integer, Integer>>() {

                public Graph<Integer, Integer>
                transform(GraphMetadata metadata) {
                    return new
                            DirectedSparseGraph<Integer, Integer>();
                }
            };
            /* Create the Vertex Transformer */
            Transformer<NodeMetadata, Integer> vertexTransformer
                    = new Transformer<NodeMetadata, Integer>() {
                public Integer transform(NodeMetadata metadata) {
                    return nodes++;
                }
            };

            /* Create the Edge Transformer */
            Transformer<EdgeMetadata, Integer> edgeTransformer =
                    new Transformer<EdgeMetadata, Integer>() {
                        public Integer transform(EdgeMetadata metadata) {
                            return edges++;
                        }
                    };
/* Create the Hyperedge Transformer */
            Transformer<HyperEdgeMetadata, Integer> hyperEdgeTransformer =
                    new Transformer<HyperEdgeMetadata, Integer>() {
                        public Integer transform(HyperEdgeMetadata metadata) {
                            return edges++;
                        }
                    };

            /* Create the graphMLReader2 */
            GraphMLReader2<Graph<Integer, Integer>, Integer, Integer>
                    graphReader = new
                    GraphMLReader2<Graph<Integer, Integer>, Integer, Integer>
                    (fileReader, graphTransformer, vertexTransformer,
                            edgeTransformer, hyperEdgeTransformer);

            try {
    /* Get the new graph object from the GraphML file */
                g = graphReader.readGraph();
            } catch (GraphIOException ex) {}

        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
    }

    public static void compute() throws IOException {
        System.out.println("Starting computing");

//        DirectedSparseGraph<String, Integer> graph = new DirectedSparseGraph<String, Integer>();
//        BufferedReader data = new BufferedReader(new InputStreamReader(new FileInputStream(input)));

        long start = System.currentTimeMillis() ;
        PageRank<Integer, Integer> ranker = new PageRank<Integer, Integer>(g, 0.85d);
//        ranker.setTolerance(this.tolerance) ;
//        ranker.setMaxIterations(this.maxIterations);

        ranker.evaluate();

//        LOG.debug ("Tolerance = " + ranker.getTolerance() );
//        LOG.debug ("Dump factor = " + (1.00d - ranker.getAlpha() ) ) ;
//        LOG.debug ("Max iterations = " + ranker.getMaxIterations() ) ;
        System.out.println("PageRank computed in " + (System.currentTimeMillis() - start)/1000.0 + " s");

//        MemoryUtil.printUsedMemory() ;

//        Map<Node, Double> result = new HashMap<Node, Double>();
//        for (String v : graph.getVertices()) {
//            result.put(new Node(v), ranker.getVertexScore(v));
//        }
//        return result;
    }
}
