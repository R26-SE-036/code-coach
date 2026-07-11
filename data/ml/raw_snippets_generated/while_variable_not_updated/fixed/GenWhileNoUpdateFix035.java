public class GenWhileNoUpdateFix035 {
    static int gather(int steps, int points) {
        int sum = 0;
        while (steps < points) {
            sum += steps;
            steps++;
        }
        return sum;
    }
}
