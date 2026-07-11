public class GenWhileNoUpdateFix132 {
    static int gather(int count, int steps) {
        int sum = 0;
        while (count < steps) {
            sum += count;
            count++;
        }
        return sum;
    }
}
