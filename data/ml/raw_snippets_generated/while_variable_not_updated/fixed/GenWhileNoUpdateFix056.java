public class GenWhileNoUpdateFix056 {
    static int gather(int steps, int limit) {
        int sum = 0;
        while (steps < limit) {
            sum += steps;
            steps++;
        }
        return sum;
    }
}
