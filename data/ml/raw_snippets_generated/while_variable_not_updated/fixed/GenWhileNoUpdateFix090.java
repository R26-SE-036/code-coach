public class GenWhileNoUpdateFix090 {
    static int gather(int total, int stock) {
        int sum = 0;
        while (total < stock) {
            sum += total;
            total++;
        }
        return sum;
    }
}
