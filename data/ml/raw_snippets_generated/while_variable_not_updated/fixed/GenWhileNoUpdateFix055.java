public class GenWhileNoUpdateFix055 {
    static void pump(boolean done, int quota) {
        while (!done) {
            System.out.println(quota);
            quota++;
            done = quota > 10;
        }
    }
}
