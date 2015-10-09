import disq
import json
import logging

def json_deserializer(bytes):
    """ This function deserializes json when the input is a sequence of
        bytes.

        :params bytes:  The input bytestring to deserialize.
        :returns:       A Python dictionary
    """
    return json.loads(bytes.decode('utf8'))

class TaskMux:
    def __init__(self, **kwargs):
        """ Create a high-level task multiplexer on top of Disque.

            :params kwargs:     These are keyword arguments to the
                                disque connection. The most commonly
                                used ones will be `host` and `port`.
        """
        self.conn = disq.Disque(**kwargs)
        self.__logger = logging.getLogger(__name__)

    def inspect_job(self, job_id):
        """ This function inspects the contents of a job.

            :params job_id:     The job to inspect
            :returns:           A dictionary of attributes
        """
        job_object = {}
        key, value = None, None
        properties = self.conn.show(job_id)
        for i, elem in enumerate(properties):
            if i % 2 == 0:  # on even elements
                if key and value:
                    job_object[key] = value
                key = elem.decode('utf8')
            else:           # on odd elements
                value = elem.decode('utf8') if isinstance(elem, bytes) else elem
        return job_object

    def put(self, work_queue, work, serializer=json.dumps):
        """ This function puts any work object into a task queue.

            :params work_queue: A name (string) of the task queue to
                                submit work.
            :params work:       Any Python object that can be serialized
                                with the serialization function.
            :params serializer: A function that takes `work` as arugment
                                and returns a serializable str.
            :returns:           A job_id--to retrieve the object
        """
        serialized_work = serializer(work)
        self.__logger.debug("Got work: '{}'".format(serialized_work))
        job_id = self.conn.addjob(work_queue, serialized_work)
        self.__logger.debug("Created work: {}".format(job_id))
        return job_id

    def get(self, work_queue, timeout=0, deserializer=json_deserializer):
        """ This function gets an element from the queue and returns
            a tuple with the queue name, the job id, and the result
            object.

            When the `timeout` is 0, **this function is blocking**.

            :params work_queue:     A name (string) of the task queue to
                                    submit work.
            :params timeout:        The number of milliseconds to wait
                                    for the work_queue; if 0, the
                                    function blocks.
            :params deserializer:   A matching deserializer to recover
                                    the object.
        """
        self.__logger.debug("Getting job from '{}'".format(work_queue))
        job = self.conn.getjob(work_queue, timeout=timeout)
        if job:
            qname, job_id, data = job
            self.__logger.debug("Got data '{}'".format(data))
            return (qname, job_id, deserializer(data))
        return job

    def report_exception(self, job_id):
        """ This function reports an exception to disque. It stores the
            job_id and the stacktrace of the problem.

            This will dequeue the job and store the job id along with
            the traceback on a special queue named "-mux:failed-". The
            contents can be inspected with "inspect_job".

            If no exception has occurred, this function does nothing.

            The typical way to use this is:

                try:
                    _, job_id, data = mux.dequeue('myqueue')
                finally:
                    mux.report_exception(job_id)

            :params job_id:     The job that failed.
        """
        exception = sys.exc_info()
        if exception is None:
            return
        exc_type, exc_value, exc_tb = exception
        self.conn.dequeue(job_id)
        self.put("-mux:failed-", {
            "job_id": job_id,
            "traceback": traceback.format_exception(exc_type, exc_value, exc_tb)
        })

    def retrieve(self, job_id, blocking=True):
        """ This function retrieves the result of a job. The "async"
            version (with blocking=False) actually blocks for 1ms.

            :params job_id:     The job_id returned from `enqueue`.
            :params blocking:   A boolean indicating whether to block.
        """
        timeout = 0 if blocking else 1
        result = self.get(job_id, timeout)
        if result:
            _, result_id, result = result
            # acknowledge (and therefore delete) the job
            self.conn.fastack(result_id)
        return result
