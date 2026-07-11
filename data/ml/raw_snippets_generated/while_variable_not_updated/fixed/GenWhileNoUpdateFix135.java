public class GenWhileNoUpdateFix135 {
    static int gather(int quota, int stock) {
        int sum = 0;
        while (quota < stock) {
            sum += quota;
            quota++;
        }
        return sum;
    }
}
