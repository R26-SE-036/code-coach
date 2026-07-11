public class GenCleanWhileTrueBreak015 {
    static boolean isEven1(int points) {
        return points % 2 == 0;
    }

    static int drain2(int quota) {
        int handled = 0;
        while (quota > 0) {
            handled += quota;
            quota--;
        }
        return handled;
    }

    static int sum3(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }

    static int spin(int count) {
        int rounds = 0;
        while (true) {
            rounds++;
            if (rounds > count) {
                break;
            }
        }
        return rounds;
    }

    static int clamp4(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
