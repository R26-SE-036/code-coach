public class GenWhileNoUpdateFix124 {
    static int drain1(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }

    static void pump(boolean verified, int steps) {
        while (!verified) {
            System.out.println(steps);
            steps++;
            verified = steps > 10;
        }
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int drain3(int quota) {
        int handled = 0;
        while (quota > 0) {
            handled += quota;
            quota--;
        }
        return handled;
    }
}
