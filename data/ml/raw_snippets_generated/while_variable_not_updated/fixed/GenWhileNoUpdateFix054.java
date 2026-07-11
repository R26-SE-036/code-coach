public class GenWhileNoUpdateFix054 {
    static int gather(int total, int steps) {
        int sum = 0;
        while (total < steps) {
            sum += total;
            total++;
        }
        return sum;
    }
}
