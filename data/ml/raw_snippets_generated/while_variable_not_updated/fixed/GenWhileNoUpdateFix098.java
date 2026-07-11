public class GenWhileNoUpdateFix098 {
    static void pump(boolean done, int quota) {
        while (!done) {
            System.out.println(quota);
            quota++;
            done = quota > 10;
        }
    }
}
