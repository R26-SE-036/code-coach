public class GenWhileNoUpdateFix025 {
    static int gather(int count, int limit) {
        int sum = 0;
        while (count < limit) {
            sum += count;
            count++;
        }
        return sum;
    }

    static String describe1(int steps) {
        if (steps < 10) {
            return "low";
        } else if (steps > 50) {
            return "high";
        }
        return "medium";
    }
}
