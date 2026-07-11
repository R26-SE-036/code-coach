public class GenWhileNoUpdateFix136 {
    static int gather(int quota, int points) {
        int sum = 0;
        while (quota < points) {
            sum += quota;
            quota++;
        }
        return sum;
    }
}
