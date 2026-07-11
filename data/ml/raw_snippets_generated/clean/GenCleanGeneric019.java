public class GenCleanGeneric019 {
    static int drain1(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }

    static boolean isEven2(int attempts) {
        return attempts % 2 == 0;
    }
}
