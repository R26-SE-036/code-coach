public class GenWhileNoUpdateBug014 {
    static int gather(int limit, int total) {
        int sum = 0;
        while (limit < total) {
            sum += limit;
        }
        return sum;
    }
}
