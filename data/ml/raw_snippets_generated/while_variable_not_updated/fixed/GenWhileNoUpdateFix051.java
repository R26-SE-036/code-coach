public class GenWhileNoUpdateFix051 {
    static void countdown(int steps) {
        while (steps > 0) {
            System.out.println("left: " + steps);
            steps--;
        }
    }

    static int drain1(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }
}
