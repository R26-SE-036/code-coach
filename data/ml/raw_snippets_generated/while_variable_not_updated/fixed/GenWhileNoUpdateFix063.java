public class GenWhileNoUpdateFix063 {
    static boolean isEven1(int steps) {
        return steps % 2 == 0;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void pump(boolean ready, int limit) {
        while (!ready) {
            System.out.println(limit);
            limit++;
            ready = limit > 10;
        }
    }

    static void printAll4(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }
}
