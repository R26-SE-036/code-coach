public class GenWhileNoUpdateBug081 {
    static String describe1(int budget) {
        if (budget < 100) {
            return "low";
        } else if (budget > 500) {
            return "high";
        }
        return "medium";
    }

    static int drain2(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static int drain3(int quota) {
        int handled = 0;
        while (quota > 0) {
            handled += quota;
            quota--;
        }
        return handled;
    }

    static void pump(boolean enabled, int quota) {
        while (!enabled) {
            System.out.println(quota);
            quota++;
        }
    }
}
