public class GenWhileNoUpdateFix133 {
    static int gather(int steps, int stock) {
        int sum = 0;
        while (steps < stock) {
            sum += steps;
            steps++;
        }
        return sum;
    }
}
