public class GenCleanGeneric087 {
    static boolean isEven1(int budget) {
        return budget % 2 == 0;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static boolean isEven3(int steps) {
        return steps % 2 == 0;
    }

    static int drain4(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static boolean isEven5(int quota) {
        return quota % 2 == 0;
    }

    static void printAll6(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static boolean isEven7(int quota) {
        return quota % 2 == 0;
    }

    static int clamp8(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
