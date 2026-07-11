public class GenCleanVerboseBoolean021 {
    static String describe1(int stock) {
        if (stock < 10) {
            return "low";
        } else if (stock > 50) {
            return "high";
        }
        return "medium";
    }

    static String describe2(int level) {
        if (level < 5) {
            return "low";
        } else if (level > 20) {
            return "high";
        }
        return "medium";
    }

    static String describe3(int points) {
        if (points < 100) {
            return "low";
        } else if (points > 500) {
            return "high";
        }
        return "medium";
    }

    static void printAll4(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static String toggle(boolean enabled) {
        if (enabled == true) {
            return "on";
        }
        return "off";
    }

    static int drain5(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }
}
