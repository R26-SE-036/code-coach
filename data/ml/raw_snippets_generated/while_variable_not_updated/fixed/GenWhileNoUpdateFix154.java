public class GenWhileNoUpdateFix154 {
    static void pump(boolean done, int steps) {
        while (!done) {
            System.out.println(steps);
            steps++;
            done = steps > 10;
        }
    }
}
