public class GenArrayIndexBug160 {
    static void showLast(int[] weights) {
        System.out.println(weights[weights.length]);
    }

    static int drain1(int level) {
        int handled = 0;
        while (level > 0) {
            handled += level;
            level--;
        }
        return handled;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static boolean isEven3(int total) {
        return total % 2 == 0;
    }

    static int drain4(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static int drain5(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }

    static boolean isEven6(int total) {
        return total % 2 == 0;
    }

    static String status7(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static int average8(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
