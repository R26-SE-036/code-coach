public class GenWhileNoUpdateFix129 {
    static void pump(boolean done, int limit) {
        while (!done) {
            System.out.println(limit);
            limit++;
            done = limit > 10;
        }
    }
}
