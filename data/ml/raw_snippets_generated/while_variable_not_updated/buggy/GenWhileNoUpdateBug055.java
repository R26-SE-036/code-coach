public class GenWhileNoUpdateBug055 {
    static void pump(boolean done, int quota) {
        while (!done) {
            System.out.println(quota);
            quota++;
        }
    }
}
