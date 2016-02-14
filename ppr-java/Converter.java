import java.io.File;
import java.io.FileNotFoundException;
import java.util.Scanner;

public class Converter {
//    public static void main(String[] args) {
//        System.out.println(find_max("blorg"));
//    }
    static int N = 0;

    static int find_max(String fname) {
        int max = -1;
        try {
            Scanner sc = new Scanner(new File(fname));
            while(sc.hasNextLine()) {
                Scanner sc2 = new Scanner(sc.nextLine());
                int from_node = sc2.nextInt();
                N++;
//                if (from_node > max) {
//                    max = from_node;
//                }
                sc2.skip(" : ");
                while (sc2.hasNextInt()) {
                    int n = sc2.nextInt();
                        N++;
//                    System.out.println("Read" + n);
//                    if (n > max) {
//                        max = n;
//                    }
                }
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
        return max;
    }
}