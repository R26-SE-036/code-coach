public class GenWhileNoUpdateFix042 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int gather(int steps, int limit) {
        int sum = 0;
        while (steps < limit) {
            sum += steps;
            steps++;
        }
        return sum;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
