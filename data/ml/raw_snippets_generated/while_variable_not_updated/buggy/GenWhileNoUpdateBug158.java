public class GenWhileNoUpdateBug158 {
    static void pump(boolean running, int steps) {
        while (!running) {
            System.out.println(steps);
            steps++;
        }
    }
}
