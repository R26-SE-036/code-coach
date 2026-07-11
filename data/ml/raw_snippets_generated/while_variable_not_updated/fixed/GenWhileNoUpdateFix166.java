public class GenWhileNoUpdateFix166 {
    static int gather(int steps, int budget) {
        int sum = 0;
        while (steps < budget) {
            sum += steps;
            steps++;
        }
        return sum;
    }
}
