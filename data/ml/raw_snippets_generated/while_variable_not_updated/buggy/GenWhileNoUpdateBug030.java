public class GenWhileNoUpdateBug030 {
    static void pump(boolean running, int budget) {
        while (!running) {
            System.out.println(budget);
            budget++;
        }
    }
}
