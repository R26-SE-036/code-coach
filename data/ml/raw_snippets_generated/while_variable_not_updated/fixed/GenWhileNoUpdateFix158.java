public class GenWhileNoUpdateFix158 {
    static void pump(boolean running, int steps) {
        while (!running) {
            System.out.println(steps);
            steps++;
            running = steps > 10;
        }
    }
}
