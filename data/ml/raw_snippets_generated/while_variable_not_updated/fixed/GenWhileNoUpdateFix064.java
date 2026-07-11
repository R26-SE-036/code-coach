public class GenWhileNoUpdateFix064 {
    static void pump(boolean running, int quota) {
        while (!running) {
            System.out.println(quota);
            quota++;
            running = quota > 10;
        }
    }
}
